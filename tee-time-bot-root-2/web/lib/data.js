// Sample tee time data modeled after the backend
export const COURSES = [
  { id:'cog_hill_4', name:'Cog Hill #4', short:'Dubsdread', tier:'A+', city:'Lemont', distance:28, dir:'SW', platform:'ForeUp' },
  { id:'cantigny',  name:'Cantigny Golf', short:'Lakeside/Woodside', tier:'A+', city:'Wheaton', distance:30, dir:'W', platform:'Whoosh' },
  { id:'mistwood',  name:'Mistwood', short:'Golf Club', tier:'A+', city:'Romeoville', distance:35, dir:'SW', platform:'CPS' },
  { id:'harborside',name:'Harborside International', short:'Port Course', tier:'A+', city:'Chicago', distance:15, dir:'S', platform:'GolfNow' },
  { id:'seven_bridges', name:'Seven Bridges', short:'Golf Club', tier:'A+', city:'Woodridge', distance:28, dir:'W', platform:'GolfNow' },
  { id:'thunderhawk', name:'Thunderhawk', short:'Golf Club', tier:'A+', city:'Beach Park', distance:50, dir:'N', platform:'GolfNow' },
  { id:'bolingbrook', name:'Bolingbrook', short:'Golf Club', tier:'A+', city:'Bolingbrook', distance:34, dir:'SW', platform:'GolfNow' },
  { id:'glen_club', name:'The Glen Club', short:'Tom Fazio', tier:'A+', city:'Glenview', distance:20, dir:'N', platform:'EZLinks' },
];

export const TEE_TIMES = [
  { id:'t1', course:'cog_hill_4', date:'2026-04-25', day:'SAT', time:'06:42',
    price:98, players:2, slotsLeft:3, score:96, rank:1,
    signals:['prime','rare'], wx:'sun', temp:58, wind:6, sunrise:'06:12',
    reason:'Prime tee window on your #1 course · under budget' },
  { id:'t2', course:'cantigny', date:'2026-04-25', day:'SAT', time:'07:12',
    price:115, players:4, slotsLeft:4, score:93, rank:2,
    signals:['prime'], wx:'sun', temp:61, wind:8, sunrise:'06:12',
    reason:'Full foursome · 27-hole favorite' },
  { id:'t3', course:'mistwood', date:'2026-04-26', day:'SUN', time:'06:58',
    price:125, players:2, slotsLeft:2, score:91, rank:3,
    signals:['deal'], wx:'cloud', temp:54, wind:12, sunrise:'06:10',
    reason:'$30 under typical Sunday rate' },
  { id:'t4', course:'harborside', date:'2026-04-25', day:'SAT', time:'08:24',
    price:89, players:4, slotsLeft:4, score:84, rank:4,
    signals:['deal'], wx:'sun', temp:63, wind:10, sunrise:'06:12',
    reason:'City-adjacent · 15 min drive' },
  { id:'t5', course:'seven_bridges', date:'2026-04-26', day:'SUN', time:'07:48',
    price:109, players:3, slotsLeft:2, score:79, rank:5,
    signals:[], wx:'wind', temp:55, wind:16, sunrise:'06:10',
    reason:'Solid Sunday window' },
  { id:'t6', course:'thunderhawk', date:'2026-04-27', day:'MON', time:'09:06',
    price:62, players:2, slotsLeft:4, score:66, rank:6,
    signals:['deal'], wx:'drizzle', temp:49, wind:14, sunrise:'06:08',
    reason:'Deep midweek discount' },
];

export const ALERTS = [
  { id:'a1', kind:'snipe',  title:'Autobook confirmed', course:'Cog Hill #4', time:'Sat Apr 25 · 6:42am', body:'Locked in at $98. Confirmation #CH-8821.', age:'2m', state:'success' },
  { id:'a2', kind:'new',    title:'New PRIME match', course:'Cantigny · Lakeside', time:'Sat Apr 25 · 7:12am', body:'Score 93 · fits Saturday early window', age:'18m' },
  { id:'a3', kind:'deal',   title:'Price drop', course:'Mistwood', time:'Sun Apr 26 · 6:58am', body:'$155 → $125 · rare for Sunday AM', age:'41m' },
  { id:'a4', kind:'rare',   title:'Rare window opened', course:'Harborside Port', time:'Sat Apr 25 · 6:30am', body:'First tee on a Saturday. Act fast.', age:'1h' },
  { id:'a5', kind:'digest', title:"Today's top 5", course:'Daily digest', time:'6:00am', body:'We scanned 40 courses. 12 PRIME matches found.', age:'5h' },
];

export const SNIPES = [
  { id:'s1', course:'Cog Hill #4', date:'Sat Apr 25', time:'06:30–07:00', players:2, maxPrice:120, state:'armed',   fires:'Fri 5:30pm' },
  { id:'s2', course:'Cantigny',    date:'Sun Apr 26', time:'06:45–07:30', players:4, maxPrice:130, state:'scanning', fires:'live' },
  { id:'s3', course:'Mistwood',    date:'Sat May 02', time:'06:00–08:00', players:2, maxPrice:140, state:'booked',   fires:'booked 06:58' },
  { id:'s4', course:'Harborside',  date:'Mon Apr 27', time:'any',         players:3, maxPrice:80,  state:'armed',    fires:'Sun 5:30pm' },
];

export const courseById = Object.fromEntries(COURSES.map(c => [c.id, c]));
